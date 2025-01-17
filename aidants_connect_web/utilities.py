import hashlib
import io
from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union
from urllib.parse import quote, urlencode

from django.conf import settings
from django.db import transaction
from django.db.models import F

import qrcode

if TYPE_CHECKING:
    from aidants_connect_web.models import Aidant, Usager


@transaction.atomic
def generate_new_datapass_id() -> int:
    from .models import IdGenerator

    id_datapass = IdGenerator.objects.select_for_update().get(
        code=settings.DATAPASS_CODE_FOR_ID_GENERATOR
    )

    id_datapass.last_id = F("last_id") + 1
    id_datapass.save()
    id_datapass.refresh_from_db()
    return id_datapass.last_id


def generate_sha256_hash(value: bytes):
    """
    Generate a SHA-256 hash
    https://docs.python.org/3/library/hashlib.html
    SHA-256 is a hash function that takes bytes as input, and returns a hash
    The length of the hash is 64 characters
    To add a salt, concatenate the string with the salt ('string'+'salt')
    You must encode your string to bytes beforehand ('stringsalt'.encode())
    :param value: bytes
    :return: a hash (string) of 64 characters
    """
    return hashlib.sha256(value).hexdigest()


def generate_file_sha256_hash(filename):
    """
    Generate a SHA-256 hash of a file
    """
    base_path = Path(__file__).resolve().parent
    file_path = (base_path / filename).resolve()
    with open(file_path, "rb") as f:
        file_bytes = f.read()  # read entire file as bytes
        file_readable_hash = generate_sha256_hash(file_bytes)
        return file_readable_hash


def validate_attestation_hash(attestation_string, attestation_hash):
    attestation_string_with_salt = attestation_string + settings.ATTESTATION_SALT
    new_attestation_hash = generate_sha256_hash(
        attestation_string_with_salt.encode("utf-8")
    )
    return new_attestation_hash == attestation_hash


def generate_qrcode_png(string: str):
    stream = io.BytesIO()
    img = qrcode.make(string)
    img.save(stream, "PNG")
    return stream.getvalue()


def generate_attestation_hash(
    aidant: "Aidant",
    usager: "Usager",
    demarches: Union[str, list],
    expiration_date: datetime,
    creation_date: str = date.today().isoformat(),
    mandat_template_path: str = settings.MANDAT_TEMPLATE_PATH,
    organisation_id: Optional[int] = None,
):
    organisation_id = (
        aidant.organisation.id if organisation_id is None else organisation_id
    )

    if isinstance(demarches, str):
        demarches_list = demarches
    else:
        demarches.sort()
        demarches_list = ",".join(demarches)

    attestation_data = {
        "aidant_id": aidant.id,
        "creation_date": creation_date,
        "demarches_list": demarches_list,
        "expiration_date": expiration_date.date().isoformat(),
        "organisation_id": organisation_id,
        "template_hash": generate_file_sha256_hash(f"templates/{mandat_template_path}"),
        "usager_sub": usager.sub,
    }
    sorted_attestation_data = dict(sorted(attestation_data.items()))
    attestation_string = ";".join(
        str(x) for x in list(sorted_attestation_data.values())
    )
    attestation_string_with_salt = attestation_string + settings.ATTESTATION_SALT
    return generate_sha256_hash(attestation_string_with_salt.encode("utf-8"))


def generate_mailto_link(recipient: str, subject: str, body: str):
    urlencoded = urlencode(
        {"subject": subject, "body": body},
        quote_via=lambda x, _, enc, err: quote(x, "", enc, err),
    )
    return f"mailto:{recipient}?{urlencoded}"


def mandate_template_path():
    return settings.MANDAT_TEMPLATE_PATH
