import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))
import ado_cli


class TestAdoCli(unittest.TestCase):

    def test_extract_parent_id(self):
        item = {
            "id": 123,
            "relations": [
                {
                    "attributes": {"name": "Parent"},
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/696"
                }
            ]
        }
        self.assertEqual(ado_cli.extract_parent_id(item), 696)

    def test_extract_parent_id_none(self):
        item = {"id": 123, "relations": []}
        self.assertIsNone(ado_cli.extract_parent_id(item))

    @patch("ado_cli.show_work_item")
    def test_find_child_task_by_title_found(self, mock_show):
        # Parent returns a child relation pointing to 801
        mock_show.side_effect = [
            # 1. Parent
            {
                "id": 696,
                "relations": [
                    {
                        "attributes": {"name": "Child"},
                        "rel": "System.LinkTypes.Hierarchy-Forward",
                        "url": "https://dev.azure.com/org/proj/_apis/wit/workItems/801"
                    }
                ]
            },
            # 2. Child 801
            {
                "id": 801,
                "fields": {"System.Title": "Target Title"}
            }
        ]
        found_id = ado_cli.find_child_task_by_title(696, "Target Title", "org", "proj", {})
        self.assertEqual(found_id, 801)

    @patch("ado_cli.show_work_item")
    def test_find_child_task_by_title_not_found(self, mock_show):
        mock_show.return_value = {"id": 696, "relations": []}
        found_id = ado_cli.find_child_task_by_title(696, "Non Existent", "org", "proj", {})
        self.assertIsNone(found_id)

    @patch("ado_cli.find_child_task_by_title")
    def test_create_task_dry_run(self, mock_find):
        mock_find.return_value = None
        # In dry run, create_task returns None and executes no write
        res = ado_cli.create_task(696, "Test Title", "cr-004", "org", "proj", dry_run=True, env={})
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
