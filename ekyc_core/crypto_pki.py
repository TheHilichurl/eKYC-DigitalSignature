import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

class CryptoPKI:
    @staticmethod
    def generate_key_pair(key_size=2048):
        """Generates an RSA Asymmetric Keypair."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        return private_pem, public_pem

    @staticmethod
    def load_private_key(private_pem: str):
        return serialization.load_pem_private_key(
            private_pem.encode('utf-8'),
            password=None
        )

    @staticmethod
    def load_public_key(public_pem: str):
        return serialization.load_pem_public_key(
            public_pem.encode('utf-8')
        )

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        """Returns lowercase hex digest of SHA-256."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def sign_data(data: bytes, private_pem: str) -> str:
        """
        Signs arbitrary binary data (or document bytes) using RSA-PSS SHA-256.
        Returns signature encoded in hex.
        """
        private_key = CryptoPKI.load_private_key(private_pem)
        signature = private_key.sign(
            data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature.hex()

    @staticmethod
    def verify_signature(data: bytes, signature_hex: str, public_pem: str) -> bool:
        """
        Verifies if data matches the digital signature using the signer's Public Key.
        Returns True if completely authentic, False if document was altered/tampered.
        """
        try:
            public_key = CryptoPKI.load_public_key(public_pem)
            signature = bytes.fromhex(signature_hex)
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except (InvalidSignature, ValueError):
            return False

