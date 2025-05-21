import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import requests # Required for requests.exceptions.RequestException

# Add project root to sys.path to allow importing from prompt_and_response
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prompt_and_response import validate_skill_input, verify_url, InvalidInputError

class TestPromptAndResponse(unittest.TestCase):

    def test_validate_skill_input(self):
        self.assertEqual(validate_skill_input("Python"), "Python")
        self.assertEqual(validate_skill_input("  Data Analysis  "), "Data Analysis")
        with self.assertRaises(InvalidInputError):
            validate_skill_input("")
        with self.assertRaises(InvalidInputError):
            validate_skill_input("  ")
        with self.assertRaises(InvalidInputError):
            validate_skill_input("Py")

    @patch('prompt_and_response.requests.head')
    def test_verify_url_valid(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response
        self.assertTrue(verify_url("http://example.com"))
        mock_head.assert_called_once_with("http://example.com", timeout=5, allow_redirects=True)

    @patch('prompt_and_response.requests.head')
    def test_verify_url_invalid_format(self, mock_head):
        self.assertFalse(verify_url("notaurl"))
        mock_head.assert_not_called()

    @patch('prompt_and_response.requests.head')
    def test_verify_url_404(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response
        self.assertFalse(verify_url("http://example.com/notfound"))
        mock_head.assert_called_once_with("http://example.com/notfound", timeout=5, allow_redirects=True)

    @patch('prompt_and_response.requests.head')
    def test_verify_url_request_exception(self, mock_head):
        mock_head.side_effect = requests.exceptions.RequestException
        self.assertFalse(verify_url("http://example.com/exception"))
        mock_head.assert_called_once_with("http://example.com/exception", timeout=5, allow_redirects=True)

if __name__ == '__main__':
    unittest.main()
