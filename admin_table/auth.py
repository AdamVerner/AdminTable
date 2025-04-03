import abc
import dataclasses
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

JWT_SIGN_KEY = str(uuid.uuid4())


class AuthException(Exception):
    pass


class InvalidAccessTokenException(AuthException):
    pass


class InvalidCredentialsException(AuthException):
    pass


class MissingCapabilitiesException(AuthException):
    pass


class MissingOTPException(AuthException):
    pass


class TokenTypes:
    access = "acc"
    refresh = "ref"


class AuthHelpers:
    access_expiration = timedelta(minutes=1)
    refresh_expiration = timedelta(minutes=5)
    sign_key = JWT_SIGN_KEY
    sign_algo = "HS256"

    def _encoded(self, payload: dict[str, Any], token_type: str, expire_in: timedelta) -> str:
        full_payload = {
            "iat": datetime.now(timezone.utc).timestamp(),
            "exp": (datetime.now(timezone.utc) + expire_in).timestamp(),
            "typ": token_type,
            **payload,
        }
        encoded_jwt = jwt.encode(full_payload, self.sign_key, algorithm=self.sign_algo)
        return encoded_jwt

    def _decoded(self, token, expected_typ: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(token, self.sign_key, algorithms=[self.sign_algo])
        except jwt.ExpiredSignatureError:
            raise InvalidAccessTokenException("Access token has expired.")
        except jwt.InvalidTokenError as e:
            raise InvalidAccessTokenException(f"Invalid access token.: {e}")

        if payload.get("typ") != expected_typ:
            raise InvalidAccessTokenException("Invalid token type.")

        if not payload.get("sub"):
            raise InvalidAccessTokenException("Invalid access token. Does not contain sub.")

        if not payload.get("display"):
            raise InvalidAccessTokenException("Invalid access token. Does not contain display.")

        return payload

    def generate_access_token(self, user_id: str, display: str, capabilities: list[str]):
        payload = {
            "sub": user_id,
            "display": display,
            "cap": capabilities,
        }
        return self._encoded(payload, TokenTypes.access, expire_in=self.access_expiration)

    def generate_refresh_token(self, user_id: str, display: str):
        payload = {
            "sub": user_id,
            "display": display,
            "jti": str(uuid.uuid4()),
        }
        return self._encoded(payload, TokenTypes.refresh, expire_in=self.refresh_expiration)

    @dataclasses.dataclass
    class DecodedAccessToken:
        user_id: str
        display: str
        capabilities: list[str]

    def decode_access_token(self, access_token: str) -> DecodedAccessToken:
        payload = self._decoded(access_token, expected_typ=TokenTypes.access)

        if not (cap := payload.get("cap")):
            raise InvalidAccessTokenException("Invalid access token. Does not contain cap.")

        return self.DecodedAccessToken(
            user_id=payload["sub"],
            display=payload["display"],
            capabilities=cap,
        )

    @dataclasses.dataclass
    class DecodedRefreshToken:
        user_id: str
        display: str
        jwt_id: str
        expiry: datetime

    def decode_refresh_token(self, refresh_token: str) -> DecodedRefreshToken:
        payload = self._decoded(refresh_token, expected_typ=TokenTypes.refresh)

        expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        return self.DecodedRefreshToken(
            user_id=payload["sub"],
            display=payload["display"],
            jwt_id=payload["jti"],
            expiry=expiry,
        )


class AuthProviderBase(abc.ABC, AuthHelpers):
    @dataclasses.dataclass
    class AuthInfo:
        access_token: str
        refresh_token: str
        capabilities: list[str]
        token_lifetime: int  # seconds until access token expiry

    # ######
    # Set of functions implemented by the library user
    # ######
    @dataclasses.dataclass
    class UserInfo:
        user_id: str
        display: str

    @abc.abstractmethod
    async def authenticate(self, username: str | None, password: str | None, otp: str | None) -> UserInfo:
        """
        Check validity of the credentials and return user identification which can be used later to authorize the user.
        If user has set up OTP authentication, but `otp` parameter is not provided, the method should raise `MissingOTPException`
        If invalid username and password combination is provided, the method should raise `InvalidCredentialsException`
        """
        raise NotImplementedError()

    @abc.abstractmethod
    async def authorize(self, user_id: str) -> list[str]:
        """
        Return a set of capabilities which the user_id (provided by `authenticate` method) has.
        If User is not active anymore or choose to logout-globally this method should raise an exception.
        """
        raise NotImplementedError()

    # ######
    # set of functions used by the frontend
    # ######

    async def login(self, username: str, password: str, otp: str | None) -> AuthInfo:
        user = await self.authenticate(username, password, otp)
        capabilities = await self.authorize(user.user_id)
        return self.AuthInfo(
            access_token=self.generate_access_token(
                user_id=user.user_id, display=user.display, capabilities=capabilities
            ),
            refresh_token=self.generate_refresh_token(user_id=user.user_id, display=user.display),
            capabilities=capabilities,
            token_lifetime=int(self.access_expiration.total_seconds()),
        )

    async def refresh(self, refresh_token: str) -> AuthInfo:
        decoded_refresh_token = self.decode_refresh_token(refresh_token)

        # TODO check refresh token revocation

        capabilities = await self.authorize(decoded_refresh_token.user_id)

        if (datetime.now(timezone.utc) - decoded_refresh_token.expiry) < self.refresh_expiration / 2:
            refresh_token = self.generate_refresh_token(
                user_id=decoded_refresh_token.user_id, display=decoded_refresh_token.display
            )

        return self.AuthInfo(
            access_token=self.generate_access_token(
                user_id=decoded_refresh_token.user_id, display=decoded_refresh_token.display, capabilities=capabilities
            ),
            refresh_token=refresh_token,
            capabilities=capabilities,
            token_lifetime=int(self.access_expiration.total_seconds()),
        )

    async def logout(self, refresh_token: str):
        self.decode_refresh_token(refresh_token)
        # TODO refresh token revocation
        return

    @dataclasses.dataclass
    class AuthorizedUserInfo:
        user_id: str
        display: str
        capabilities: list[str]

    async def access(
        self, access_token: str, required_capabilities: str | list[str] | None = None
    ) -> AuthorizedUserInfo:
        """
        Check if the access token is valid and has required capabilities included.

        Returns a list of capabilities associated with the provided token
        """

        cap_set: set[str]
        if required_capabilities is None:
            cap_set = set()
        elif isinstance(required_capabilities, str):
            cap_set = {required_capabilities}
        elif isinstance(required_capabilities, list):
            cap_set = set(required_capabilities)
        else:
            raise ValueError(f"Invalid value for required_capabilities: {required_capabilities}")

        decoded_access_token = self.decode_access_token(access_token)

        # check if we have all required capabilities
        if cap_set.issuperset(decoded_access_token.capabilities):
            raise MissingCapabilitiesException(
                f"Missing permissions to access this resource. Required: {cap_set}. Available: {decoded_access_token.capabilities}"
            )

        return self.AuthorizedUserInfo(
            user_id=decoded_access_token.user_id,
            display=decoded_access_token.display,
            capabilities=decoded_access_token.capabilities,
        )


class DummyAuthProvider(AuthProviderBase):
    sign_key = "super secret"

    async def authenticate(
        self, username: str | None, password: str | None, otp: str | None
    ) -> AuthProviderBase.UserInfo:
        if not username:
            raise InvalidCredentialsException("Username is required")
        if not password:
            raise InvalidCredentialsException("Password is required")
        return self.UserInfo(user_id=username, display=username)

    async def authorize(self, user_id: str) -> list[str]:
        if user_id == "admin@admin.admin":
            return ["admin", "superuser"]
        return ["admin"]
