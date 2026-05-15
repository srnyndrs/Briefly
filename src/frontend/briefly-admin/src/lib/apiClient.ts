import axios, { AxiosHeaders } from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

const useDevProxy =
  (process.env.REACT_APP_USE_DEV_PROXY || '').toLowerCase() === 'true';

const baseURL = useDevProxy
  ? ''
  : process.env.REACT_APP_API_BASE_URL ||
    process.env.VITE_API_BASE_URL ||
    'http://localhost:8080';

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

type TokenPair = {
  accessToken?: string;
  refreshToken?: string;
};

const authBypassEnabled =
  (process.env.REACT_APP_AUTH_BYPASS_ENABLED || '').toLowerCase() === 'true';

const authLoginPath = process.env.REACT_APP_AUTH_LOGIN_PATH;
const authRefreshPath = process.env.REACT_APP_AUTH_REFRESH_PATH;
const authEmail = process.env.REACT_APP_AUTH_EMAIL;
const authUsername = process.env.REACT_APP_AUTH_USERNAME;
const authPassword = process.env.REACT_APP_AUTH_PASSWORD;

let accessToken = process.env.REACT_APP_AUTH_ACCESS_TOKEN;
let refreshToken = process.env.REACT_APP_AUTH_REFRESH_TOKEN;

const authHttp = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const setAuthorizationHeader = (
  config: InternalAxiosRequestConfig,
  token: string
): InternalAxiosRequestConfig => {
  const headers = new AxiosHeaders(config.headers);
  headers.set('Authorization', `Bearer ${token}`);
  config.headers = headers;

  return config;
};

const extractTokens = (payload: unknown): TokenPair => {
  if (!payload || typeof payload !== 'object') {
    return {};
  }

  const record = payload as Record<string, unknown>;
  const accessCandidates = [
    record.access_token,
    record.accessToken,
    record.token,
    record.jwt,
  ];
  const refreshCandidates = [record.refresh_token, record.refreshToken];

  const nextAccessToken = accessCandidates.find(
    (value): value is string => typeof value === 'string' && value.length > 0
  );
  const nextRefreshToken = refreshCandidates.find(
    (value): value is string => typeof value === 'string' && value.length > 0
  );

  return {
    accessToken: nextAccessToken,
    refreshToken: nextRefreshToken,
  };
};

const applyTokens = (tokens: TokenPair): void => {
  accessToken = tokens.accessToken || accessToken;
  refreshToken = tokens.refreshToken || refreshToken;
};

const loginWithCredentials = async (): Promise<boolean> => {
  if (!authLoginPath || !authPassword || (!authEmail && !authUsername)) {
    return false;
  }

  const loginPayload = {
    ...(authEmail ? { email: authEmail } : {}),
    ...(!authEmail && authUsername ? { username: authUsername } : {}),
    password: authPassword,
  };

  const response = await authHttp.post(authLoginPath, loginPayload);

  const tokens = extractTokens(response.data);
  if (!tokens.accessToken) {
    return false;
  }

  applyTokens(tokens);
  return true;
};

const refreshAccessToken = async (): Promise<boolean> => {
  if (!authRefreshPath || !refreshToken) {
    return false;
  }

  const response = await authHttp.post(authRefreshPath, {
    refresh_token: refreshToken,
  });

  const tokens = extractTokens(response.data);
  if (!tokens.accessToken) {
    return false;
  }

  applyTokens(tokens);
  return true;
};

export const apiClient = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    return setAuthorizationHeader(config, accessToken);
  }

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (!authBypassEnabled) {
      return Promise.reject(error);
    }

    const status = error?.response?.status as number | undefined;
    const originalRequest = error?.config as RetriableRequestConfig | undefined;

    if (status !== 401 || !originalRequest || originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const refreshed = await refreshAccessToken();
      const relogged = refreshed ? true : await loginWithCredentials();

      if (!relogged || !accessToken) {
        return Promise.reject(error);
      }

      return apiClient.request(setAuthorizationHeader(originalRequest, accessToken));
    } catch {
      return Promise.reject(error);
    }
  }
);

export const initializeApiAuth = async (): Promise<void> => {
  if (!authBypassEnabled) {
    return;
  }

  if (accessToken) {
    return;
  }

  try {
    await loginWithCredentials();
  } catch {
    // Keep boot resilient in local/dev if auth bootstrap fails.
  }
};
