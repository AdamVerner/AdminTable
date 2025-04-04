import { useEffect, useState } from 'react';
import axios, { type AxiosError, type AxiosResponse } from 'axios';
import { useNavigate } from 'react-router-dom';
import { notifications } from '@mantine/notifications';
import { authService } from '@/services/auth';

const API_URL = import.meta.env?.VITE_API_URL ?? './';

const hexDecode = function (str: string) {
  let hex, i;
  let result = '';
  for (i = 0; i < str.length; i++) {
    hex = str.charCodeAt(i).toString(16);
    result += `0${hex}`.slice(-2);
  }

  return result;
};

export class DataAPI {
  apiUrl: string;
  // constructor which takes API_URL
  constructor(apiUrl: string) {
    this.apiUrl = apiUrl;
  }

  async get<T>(url: string): Promise<T> {
    return await this._process<T>(
      axios.get<T>(this.apiUrl + url, { headers: authService.getHeaders() })
    );
  }

  async post<T>(url: string, data: any = {}): Promise<T> {
    return await this._process<T>(
      axios.post<T>(this.apiUrl + url, data, { headers: authService.getHeaders() })
    );
  }

  async patch<T>(url: string, data: any = {}): Promise<T> {
    return await this._process<T>(
      axios.patch<T>(this.apiUrl + url, data, { headers: authService.getHeaders() })
    );
  }

  async _process<T>(request: Promise<AxiosResponse<T>>): Promise<T> {
    return await request
      .then((result) => result.data)
      .catch((e: AxiosError<{ message: string }>) => {
        if (e?.response?.status === 401) {
          authService.logout();
        }

        throw new Error(e?.response?.data?.message ?? `Request failed: ${e.message}`);
      });
  }

  websocket(url: string): WebSocket {
    const ws_url = this.apiUrl.replace('http', 'ws') + url;

    const auth = authService.getHeaders().Authorization;
    if (auth) {
      return new WebSocket(ws_url, [`bearer${hexDecode(auth)}`]);
    }
    return new WebSocket(ws_url);
  }
}

type DataHead = {
  ref: string;
  display: string;
  sortable: boolean;
  sort: 'asc' | 'desc' | null;
  description: string;
};

type DataEntry =
  | string
  | {
      type: 'link';
      kind: 'detail';
      resource: string;
      value: string;
      id: string;
    }
  | {
      type: 'link';
      kind: 'table';
      resource: string;
      value: string;
      filter: {
        col: string;
        op: string;
        val: string;
      };
    };

interface ActionResponse {
  message: string;
  failed?: true;
  refresh?: true;
  redirect?:
    | { type: 'detail'; resource: string; id: string }
    | { type: 'list'; resource: string; filters: { ref: string; op: string; val: string }[] }
    | { type: 'customPage'; name: string };
}

export interface AuthInfo {
  message: string;
  access_token: string;
  refresh_token: string;
  capabilities: string[];
  token_lifetime: number;
}

export interface UserInfo {
  user_id?: string;
  display?: string;
  email: string;
  avatar_src?: string;
  capabilities: string[];
  [key: string]: any;
}

class DataService {
  data_api = new DataAPI(API_URL);

  async ping(): Promise<void> {
    await this.data_api.post('ping');
  }

  async auth_login(username: string, password: string, otp?: string): Promise<AuthInfo> {
    return await this.data_api.post('auth/login', { username, password, otp });
  }

  async auth_refresh(refresh_token: AuthInfo['refresh_token']): Promise<AuthInfo> {
    return await this.data_api.post('auth/refresh', { token: refresh_token });
  }

  async auth_logout(refresh_token: AuthInfo['refresh_token']): Promise<{
    refresh_token: string;
    access_token: string;
    valid_for: string;
    capabilities: string[];
  }> {
    return await this.data_api.post('auth/logout', { token: refresh_token });
  }

  async getUserInfo(): Promise<UserInfo> {
    return await this.data_api.get('user');
  }
  async setUserInfo(user_info: Partial<UserInfo>) {
    return await this.data_api.patch('user', user_info);
  }

  async getNavigation(): Promise<{
    name: string;
    icon_src: string | null;
    version: string | null;
    navigation: Array<{
      name: string;
      icon: string;
      links: {
        name: string;
        display: string;
        type: 'resource' | 'page';
      }[];
    }>;
  }> {
    return await this.data_api.get('navigation');
  }

  async getPage(pageId: string): Promise<{
    display: string;
    name: string;
    content: string;
    type: 'html' | 'markdown';
  }> {
    return await this.data_api.get(`page/${pageId}/view`);
  }

  async getTable(
    resourceName: string,
    o: {
      page: number;
      perPage: number;
      sort: { ref: string; dir: 'asc' | 'desc' } | null;
      filters: { ref: string; op: string; val: string }[];
    }
  ): Promise<{
    applied_filters: {
      ref: string;
      op: string;
      val: string;
      display: string;
    }[];
    available_filters: {
      ref: string;
      display: string;
    }[];
    data: DataEntry[][];
    header: DataHead[];
    meta: {
      title: string;
      description: string;
      has_create: boolean;
    };
    pagination: {
      page: number;
      per_page: number;
      total: number;
    };
  }> {
    const p = new URLSearchParams();
    if (o.page !== null) {
      p.append('page', o.page.toString());
    }
    if (o.perPage !== null) {
      p.append('per_page', o.perPage.toString());
    }
    if (o.sort !== null) {
      p.append('sort', `${o.sort.ref};${o.sort.dir}`);
    }
    for (const f of o.filters) {
      p.append('filter', `${f.ref};${f.op};${f.val}`);
    }

    return await this.data_api.get(`resource/${resourceName}/list?${p.toString()}`);
  }

  async getCreate(resourceName: string): Promise<{
    schema: any;
  }> {
    return await this.data_api.get(`resource/${resourceName}/create`);
  }

  async createResource(resourceName: string, data: any): Promise<ActionResponse> {
    return await this.data_api.post(`resource/${resourceName}/create`, data);
  }
  async getDetail(
    resourceName: string,
    id: string
  ): Promise<{
    title: string;
    description: string | null;
    fields: [DataHead, DataEntry][];
    actions: {
      title: string;
      ref: string;
      description: string;
      parameters: {
        attr: string;
        title: string;
        type: string;
        required: boolean;
        description: string | null;
      }[];
    }[];
    tables: {
      title: string;
      description: string;
      resource: string;
      filter: {
        col: string;
        op: string;
        val: string;
      };
    }[];
    graphs: {
      title: string;
      description: string;
      reference: string;
      // graph data is fetched from separate endpoint
    }[];
  }> {
    return await this.data_api.get(`resource/${resourceName}/detail/${id}`);
  }

  async executeAction(
    resourceName: string,
    id: string,
    ref: string,
    data: Record<string, any>
  ): Promise<ActionResponse> {
    return await this.data_api.post(`resource/${resourceName}/detail/${id}/action/${ref}`, {
      params: data,
    });
  }

  async getDashboard(): Promise<{
    content: string;
  }> {
    return await this.data_api.get('dashboard');
  }

  async getDetailGraph(
    resourceName: string,
    detailId: string,
    graphRef: string,
    rangeFrom: string | null,
    rangeTo: string | null
  ): Promise<{
    type: 'line' | 'bar' | 'area';
    config: {
      data: Record<string, any>[];
      dataKey: string;
      series: { name: string; color: string; [key: string]: any }[];
      [key: string]: any;
    };
  }> {
    const p = new URLSearchParams();
    if (rangeFrom !== null) {
      p.append('range_from', rangeFrom);
    }
    if (rangeTo !== null) {
      p.append('range_to', rangeTo);
    }
    return await this.data_api.get(
      `resource/${resourceName}/detail/${detailId}/graph/${graphRef}?${p.toString()}`
    );
  }

  async getInputForm(formName: string): Promise<{
    title?: string;
    description?: string;
    schema: any;
  }> {
    return await this.data_api.get(`input_form/${formName}`);
  }

  async submitInputForm(formName: string, data: any): Promise<ActionResponse> {
    return await this.data_api.post(`input_form/${formName}`, data);
  }

  getLiveDataSocket(topic: string): WebSocket {
    const query = new URLSearchParams();
    query.append('topic', topic);
    return this.data_api.websocket(`ws/live_data?${query.toString()}`);
  }
}

export function useGetData<DataReturn>(
  getDataFunction: () => Promise<DataReturn>,
  deps: any[] = [],
  reportSuccess: boolean = false
): [DataReturn | undefined, boolean, string] {
  const navigate = useNavigate();
  const [data, setData] = useState<DataReturn>();
  const [isLoading, setIsLoading] = useState(true);
  const [failed, setFailed] = useState('');

  useEffect(() => {
    // if effect was canceled before data load finished we ignore the result
    let ignore = false;

    setIsLoading(true);

    getDataFunction()
      .then((d: DataReturn) => {
        if (ignore) {
          return;
        }

        setData(d);
        setFailed('');
        if (reportSuccess) {
          notifications.show({
            title: 'SUCCESS',
            message: 'Data loaded successfully',
            color: 'blue',
          });
          // TODO extract message from data
        }
      })
      .catch((reason) => {
        if (ignore) {
          return;
        }
        setFailed(`Loading data failed ${reason}`);
        if (reason.toString().includes('Unauthorized')) {
          authService.logout().then(() => navigate('/login'));
        }

        notifications.show({
          title: 'Failed',
          message: `Failed: ${reason}`,
          color: 'red',
          autoClose: 1500,
        });
        navigate('/');
      })
      .finally(() => {
        if (ignore) {
          return;
        }

        setIsLoading(false);
      });
    return () => {
      ignore = true;
    };
  }, [...deps]);
  return [data, isLoading, failed];
}

export default new DataService();
