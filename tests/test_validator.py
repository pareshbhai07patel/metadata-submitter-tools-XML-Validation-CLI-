"""XML Validator tests."""

import unittest
import responses
from unittest.mock import patch, Mock
from click.testing import CliRunner
from pathlib import Path

from validator.__main__ import cli


class TestXMLValidator(unittest.TestCase):
    """Test for XML validator tool.

    Testing the command line functions.
    """

    TESTFILES_ROOT = Path(__file__).parent / "test_files"

    def setUp(self):
        """Initialise CLI runner and set paths to test files."""
        self.runner = CliRunner()

        # XML files and Schemas as published by ENA
        self.xml_path = self.TESTFILES_ROOT / "xml"
        self.xsd_path = self.TESTFILES_ROOT / "schemas"

    def tearDown(self):
        """Remove setup variables."""
        pass

    def test_no_args(self):
        """Test case where no args are passed."""
        result = self.runner.invoke(cli, [])

        # Exit with code 2 (UsageError)
        self.assertEqual(result.exit_code, 2)
        # The specific error message in output
        self.assertIn("Error: Missing argument 'XML_FILE'", result.output)

    def test_one_arg(self):
        """Test case where only one arg is passed."""
        filename = "SUBMISSION.xml"
        testfile = (self.xml_path / filename).as_posix()
        result = self.runner.invoke(cli, [testfile])

        # Exit with code 2 (UsageError)
        self.assertEqual(result.exit_code, 2)
        # The specific error message in output
        self.assertIn("Error: Missing argument 'SCHEMA_FILE'", result.output)

    def test_too_many_args(self):
        """Test case where three args are passed."""
        xml_name = "SUBMISSION.xml"
        xsd_name = "SRA.submission.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd, xsd])

        # Exit with code 2 (UsageError)
        self.assertEqual(result.exit_code, 2)
        # The specific error message in output
        self.assertIn("Error: Got unexpected extra argument", result.output)

    def test_bad_filepath(self):
        """Test case where an incorrect file path is given as an arg."""
        xml_name = "no_xml"
        xsd_name = "SRA.submission.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The specific error message in output
        self.assertIn("Error: Invalid value for XML_FILE", result.output)

    def test_faulty_xml_file(self):
        """Test case for xml with incorrect xml syntax."""
        xml_name = "bad_syntax.xml"
        xsd_name = "SRA.submission.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        self.assertEqual("Faulty XML or XSD file was given.\n\n", result.output)

    def test_valid_sample_file(self):
        """Test case for a valid sample xml file."""
        xml_name = "SAMPLE.xml"
        xsd_name = "SRA.sample.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        self.assertEqual("The XML file: SAMPLE.xml\nis valid.\n\n", result.output)

    def test_valid_study_file(self):
        """Test case for a valid study xml file."""
        xml_name = "STUDY.xml"
        xsd_name = "SRA.study.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        self.assertEqual("The XML file: STUDY.xml\nis valid.\n\n", result.output)

    def test_valid_submission_file(self):
        """Test case for a valid submission xml file."""
        xml_name = "SUBMISSION.xml"
        xsd_name = "SRA.submission.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        self.assertEqual("The XML file: SUBMISSION.xml\nis valid.\n\n", result.output)

    def test_invalid_submission_file(self):
        """Test case for an invalid submission xml file."""
        xml_name = "invalid_SUBMISSION.xml"
        xsd_name = "SRA.submission.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        expected = "The XML file: invalid_SUBMISSION.xml\nis invalid.\n\n"
        self.assertEqual(expected, result.output)

    def test_valid_xml_against_wrong_schema(self):
        """Test case for a valid xml file against the wrong schema."""
        xml_name = "SUBMISSION.xml"
        xsd_name = "SRA.sample.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, [xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        self.assertEqual("The XML file: SUBMISSION.xml\nis invalid.\n\n", result.output)

    def test_verbose_option(self):
        """Test verbose flag outputs some error details when XML is invalid."""
        xml_name = "invalid_SUBMISSION.xml"
        xsd_name = "SRA.submission.xsd"
        xml = (self.xml_path / xml_name).as_posix()
        xsd = (self.xsd_path / xsd_name).as_posix()
        result = self.runner.invoke(cli, ["-v", xml, xsd])

        # Exit correctly with code 0
        self.assertEqual(result.exit_code, 0)
        # The correct output is given
        self.assertIn("Error:\nfailed validating", result.output)

    def test_valid_xml_from_url(self):
        """Test validating XML from URL."""
        with responses.RequestsMock() as rsps:
            # Read one of the test files
            xml_name = "SAMPLE.xml"
            xml = (self.xml_path / xml_name).as_posix()
            f = open(xml, "rb")
            body = f.read()
            f.close()

            # Mock HTTP request with the test files as the request body
            xml_url = "http://example.com/SAMPLE.xml"
            rsps.add(responses.GET, xml_url, body=body, status=200, content_type="application/xml")
            xsd_name = "SRA.sample.xsd"
            xsd = (self.xsd_path / xsd_name).as_posix()

            result = self.runner.invoke(cli, [xml_url, xsd])
            # Exit correctly with code 0
            self.assertEqual(result.exit_code, 0)
            # The correct output is given
            self.assertIn("The XML from the URL:\n" + xml_url + "\nis valid.\n\n", result.output)

    def test_http_error(self):
        """Test when URL gives HTTP error."""
        with responses.RequestsMock() as rsps:
            # Mock error response
            xml_url = "http://example.com/error.xml"
            rsps.add(
                responses.GET, xml_url, body="<ErrorDetails></ErrorDetails>", status=400, content_type="application/xml"
            )
            xsd_name = "SRA.sample.xsd"
            xsd = (self.xsd_path / xsd_name).as_posix()

            result = self.runner.invoke(cli, [xml_url, xsd])
            # Exit correctly with code 0
            self.assertEqual(result.exit_code, 0)
            # The correct output is given
            self.assertIn("400 Client Error:", result.output)

    def test_url_to_non_xml(self):
        """Test for URL that does not return XML."""
        with responses.RequestsMock() as rsps:
            # Mock non-xml/non-plaintext response
            xml_url = "http://example.com/"
            rsps.add(responses.GET, xml_url, body="<html></html>", status=200, content_type="text/html")
            xsd_name = "SRA.sample.xsd"
            xsd = (self.xsd_path / xsd_name).as_posix()

            result = self.runner.invoke(cli, [xml_url, xsd])
            # Exit correctly with code 0
            self.assertEqual(result.exit_code, 0)
            # The correct output is given
            self.assertIn("Error: Content of the URL", result.output)

    @patch("_io.BytesIO", autospec=True)
    @patch("ftplib.FTP", autospec=True)
    def test_ftp_url(self, mock_ftp_constructor, mock_stringio):
        """Test validating with schema from FTP URL."""
        xml_name = "SUBMISSION.xml"
        xml = (self.xml_path / xml_name).as_posix()
        xsd_name = "SRA.submission.xsd"
        xsd = (self.xsd_path / xsd_name).as_posix()
        f = open(xsd, "rb")
        schema = f.read()
        f.close()

        xsd_url = "ftp://ftp.local.server/test_files/schema.xsd"
        mock_ftp = mock_ftp_constructor.return_value
        mock_stringio = Mock()
        mock_stringio.read.return_value = schema
        self.runner.invoke(cli, [xml, xsd_url])
        mock_ftp_constructor.assert_called_with("ftp.local.server")

        # enough to assert these lines are called and the coverage is achieved
        self.assertTrue(mock_ftp.login.called)
        self.assertTrue(mock_ftp.retrbinary.called)
        self.assertTrue(mock_ftp.close.called)


if __name__ == "__main__":
    unittest.main()
