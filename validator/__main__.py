"""XML Validator against XML Schema."""

from typing import Tuple
import click
import os
import requests
import xmlschema
import ftplib
from urllib.parse import urlparse
from xml.etree.ElementTree import ParseError
from io import BytesIO
from pathlib import Path

# Change environment variables for Click commands to work
os.environ["LC_ALL"] = "en_US.utf-8"
os.environ["LANG"] = "en_US.utf-8"


def _process_http_reponse(url: str, scheme: str) -> str:
    """Process response from HTTP/HTTPS url."""
    resp = requests.get(url)
    cnt_type = ["text/plain", "xml"]
    result = ""
    if resp.status_code != requests.codes.ok:
        resp.raise_for_status()
    # we only raise upon error of protocol and content type
    # content type can also be text/plain
    elif scheme in ["http", "https"] and not any(x in resp.headers["Content-Type"] for x in cnt_type):
        error = (
            f"Error: Content of the URL ({resp.url})\n" + "is not in XML format. " + "Make sure the URL is correct.\n"
        )
        raise Exception(error)
    else:
        result = resp.text
    return result


def xmlFromURL(url: str, arg_type: str) -> Tuple[str, str]:
    """Deterimine if argument is an URL and return content from the URL."""
    scheme = urlparse(url).scheme

    try:
        # Handle FTP or file URLs
        if scheme == "file":
            raise ValueError
        elif scheme == "ftp":
            host = urlparse(url).netloc
            path = urlparse(url).path
            ftp = ftplib.FTP(host)
            ftp.login()
            r = BytesIO()
            ftp.retrbinary("RETR " + path, r.write)
            byte_str = r.read()
            content = byte_str.decode("UTF-8")  # Or use the encoding you expect
            r.close()
            ftp.close()
            return content, url
        else:
            content = _process_http_reponse(url, scheme)
            return content, url

    except ValueError:
        # If argument is a file URL type or not an URL at all
        if scheme == "file":
            url = url.replace("file://", "")

        file_path = Path(url)
        if not file_path.is_file():
            error = f"Error: Invalid value for {arg_type}\n" + f"Path {url} does not exist.\n"
            raise Exception(error)
        else:
            return str(file_path.absolute()), url

    except requests.exceptions.HTTPError as err:
        # If request responds with HTTP error
        error = str(err) + "" + url + "\nMake sure the URL is correct.\n"
        raise Exception(error)

    except ftplib.Error as err:
        # If request responds with FTP error
        error = str(err) + f" ({url})\nMake sure the URL is correct.\n"
        raise Exception(error)


@click.command()
@click.argument("xml_file")
@click.argument("schema_file")
@click.option("-v", "--verbose", is_flag=True, help="Verbose printout for XML validation errors.")
def cli(xml_file: str, schema_file: str, verbose: str) -> None:
    """Validate an XML against an XSD SCHEMA."""
    xml_from_url = False

    try:
        xml_file, requested_url = xmlFromURL(xml_file, "XML_FILE")
        if not xml_file.startswith("/"):
            xml_from_url = True

        xsd_resp, _ = xmlFromURL(schema_file, "SCHEMA_FILE")
        if xsd_resp:
            schema_file = str(xsd_resp)

    except Exception as error:
        click.echo(error)
        return None

    try:
        xmlschema.validate(xml_file, schema=schema_file)  # type: ignore
        # When validation succeeds
        if xml_from_url:
            click.echo(f"The XML from the URL:\n{requested_url}")
            click.secho("is valid.\n", fg="green")
        else:
            click.echo("The XML file: " + click.format_filename(str(xml_file), shorten=True))
            click.secho("is valid.\n", fg="green")

    except xmlschema.validators.exceptions.XMLSchemaValidationError as err:
        # When validation does not succeed
        if xml_from_url:
            click.echo(f"The XML from the URL:\n{requested_url}")
            click.secho("is invalid.\n", fg="red")
        else:
            click.echo("The XML file: " + click.format_filename(str(xml_file), shorten=True))
            click.secho("is invalid.\n", fg="red")
        if verbose:
            click.secho("Error:", bold=True)
            click.echo(err)

    except ParseError as err:
        # If there is a syntax error with either file
        click.echo("Faulty XML or XSD file was given.\n")
        if verbose:
            click.echo(f"Error: {err}")

    except xmlschema.exceptions.XMLSchemaException as err:
        if not verbose:
            click.echo(
                "\nValidation ran into an unexpected error." + " Run command with --verbose option for more details\n"
            )
        else:
            click.echo(f"Error: {err}")


if __name__ == "__main__":
    cli()
    # Revert environment variables back
    os.unsetenv("LC_ALL")
    os.unsetenv("LANG")
