import pandas as pd
import pytest

from tag_tracer.config.loader import ExcelConfig, ExcelLoader, PageConfig, VendorConfig


@pytest.fixture
def mock_excel_loader(mocker):
    # Mock pandas.ExcelFile and its parse method
    mock_workbook = mocker.MagicMock()

    # Mock for 'vendors' sheet
    mock_vendors_df = pd.DataFrame(
        {
            "Key": ["domain", "query-fields", "body-fields"],
            "Value": ["example.com", "[param1,param2]", "[body1,body2]"],
        }
    )

    # Mock for 'pages' sheet
    mock_pages_df = pd.DataFrame(
        {
            "id": ["home"],
            "target-url": ["https://www.example.com"],
            "vendors": ["[vendor_a]"],
            "expected_param_1": ["value_1"],
        }
    )

    mock_workbook.sheet_names = ["vendor_a", "pages"]
    mock_workbook.parse.side_effect = lambda sheet_name: {
        "vendor_a": mock_vendors_df,
        "pages": mock_pages_df,
    }[sheet_name]

    mocker.patch("pandas.ExcelFile", return_value=mock_workbook)
    return ExcelLoader("dummy_path.xlsx")  # Path doesn't matter due to mocking


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


def test_string_to_list_utility():
    from tag_tracer.utils.utils import string_to_list

    assert string_to_list("[item1, item2]") == ["item1", "item2"]
    assert string_to_list("item1") == ["item1"]
    assert string_to_list("[]") == []
    assert string_to_list("[ item1 , item2 ]") == ["item1", "item2"]
    assert string_to_list("") == []
