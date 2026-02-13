import os
import pytest
import pandas as pd # Added import
from src.config.loader import ExcelLoader, ExcelConfig, VendorConfig, PageConfig

# Define a temporary Excel file for testing
@pytest.fixture
def temp_excel_config(tmp_path):
    excel_path = tmp_path / "test_config.xlsx"
    # Create a dummy Excel file (simplified for demonstration)
    # In a real scenario, you'd use pandas to create a more robust dummy Excel
    # For now, we just create an empty file, as loader expects sheet names
    # and will raise an error if sheets are missing.
    # We will need to mock pd.ExcelFile and its parse method for real tests.
    with open(excel_path, "w") as f:
        f.write("") # Placeholder, actual content will be mocked
    return excel_path

@pytest.fixture
def mock_excel_loader(mocker):
    # Mock pandas.ExcelFile and its parse method
    mock_workbook = mocker.MagicMock()
    
    # Mock for 'vendors' sheet
    mock_vendors_df = pd.DataFrame({
        "Key": ["domain", "query-fields", "body-fields"],
        "Value": ["example.com", "[param1,param2]", "[body1,body2]"]
    })
    
    # Mock for 'pages' sheet
    mock_pages_df = pd.DataFrame({
        "id": ["home"],
        "target-url": ["https://www.example.com"],
        "vendors": ["[vendor_a]"],
        "expected_param_1": ["value_1"]
    })

    mock_workbook.sheet_names = ["vendor_a", "pages"]
    mock_workbook.parse.side_effect = lambda sheet_name: {
        "vendor_a": mock_vendors_df,
        "pages": mock_pages_df
    }[sheet_name]

    mocker.patch("pandas.ExcelFile", return_value=mock_workbook)
    return ExcelLoader("dummy_path.xlsx") # Path doesn't matter due to mocking

def test_excel_loader_initialization_file_not_found():
    with pytest.raises(FileNotFoundError):
        ExcelLoader("non_existent_file.xlsx")

def test_excel_loader_load_method(mock_excel_loader):
    config = mock_excel_loader.load()

    assert isinstance(config, ExcelConfig)
    assert "vendor_a" in config.vendors
    assert isinstance(config.vendors["vendor_a"], VendorConfig)
    assert config.vendors["vendor_a"].domains == ["example.com"]
    assert config.vendors["vendor_a"].query_fields == ["param1", "param2"]
    assert config.vendors["vendor_a"].body_fields == ["body1", "body2"]

    assert len(config.pages) == 1
    assert isinstance(config.pages[0], PageConfig)
    assert config.pages[0].id == "home"
    assert config.pages[0].target_url == "https://www.example.com"
    assert config.pages[0].page_vendors == ["vendor_a"]
    assert config.pages[0].expected_tags == {"expected_param_1": "value_1"}

def test_parse_string_list_utility():
    from src.config.loader import _parse_string_list
    assert _parse_string_list("[item1, item2]") == ["item1", "item2"]
    assert _parse_string_list("item1") == ["item1"]
    assert _parse_string_list("[]") == []
    assert _parse_string_list("[ item1 , item2 ]") == ["item1", "item2"]
    assert _parse_string_list("") == [""] # Should be handled by string_to_list or other validation

# It is important to also mock the `string_to_list` in src.config.loader
# as it's imported from src.utils.utils but used in src.config.loader.
# If we were to run this test standalone, it would try to import
# `string_to_list` from the actual `src.utils.utils` module.
def test_string_to_list_mocked(mocker, mock_excel_loader):
    mocker.patch("src.utils.utils.string_to_list", side_effect=lambda x: [x.strip("[]")])
    # Re-instantiate or reload the module if necessary to pick up the mock
    # For now, relying on mock_excel_loader's setup
    config = mock_excel_loader.load()
    assert config.pages[0].page_vendors == ["vendor_a"]