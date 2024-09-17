import { useEffect, useState } from 'react';
import axios, { type AxiosError, type AxiosResponse } from 'axios';
import { notifications } from '@mantine/notifications';
import { authService } from '@/services/auth';

const API_URL = import.meta.env?.VITE_API_URL ?? './';

export const operators = {
  eq: '=',
  ne: '!=',
  lt: '<',
  le: '<=',
  gt: '>',
  ge: '>=',
  in: 'in',
  like: 'like',
  ilike: 'ilike',
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
}

type DataHead = {
  ref: string;
  display: string;
  sortable: boolean;
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

class DataService {
  data_api = new DataAPI(API_URL);

  async ping(): Promise<void> {
    await this.data_api.post('ping');
  }

  async login(username: string, password: string): Promise<{ token: string }> {
    return await this.data_api.post('login', { username, password});
  }

  async getUserInfo(): Promise<{
    user: {name?: string; email: string; avatar?: string}
  }> {
    return await this.data_api.get('user');
  }

  async getNavigation(): Promise<{
    name: string;
    links: Array<{
      name: string;
      children: {
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

  async createResource(
    resourceName: string,
    data: any
  ): Promise<{
    message: string;
    failed?: true;
    redirect?:
      | { type: 'detail'; resource: string; id: string }
      | { type: 'table'; resource: string; filters: { ref: string; op: string; val: string }[] }
      | { type: 'customPage'; name: string };
  }> {
    return await this.data_api.post(`resource/${resourceName}/create`, data);
  }
  async getDetail(
    resourceName: string,
    id: string
  ): Promise<{
    title: string;
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
  }> {
    return await this.data_api.get(`resource/${resourceName}/detail/${id}`);
  }

  async executeAction(
    resourceName: string,
    id: string,
    ref: string,
    data: Record<string, any>
  ): Promise<{ message: string; failed?: boolean }> {
    return await this.data_api.post(`resource/${resourceName}/detail/${id}/action/${ref}`, {
      params: data,
    });
  }

  async getBanner(): Promise<{
    content: string;
  }> {
    return await this.data_api.get('banner');
  }
}

export function useGetData<DataReturn>(
  getDataFunction: () => Promise<DataReturn>,
  deps: any[] = [],
  reportSuccess: boolean = false
): [DataReturn | undefined, boolean, string] {
  const [data, setData] = useState<DataReturn>();
  const [isLoading, setIsLoading] = useState(false);
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
        notifications.show({
          title: 'Failed',
          message: `Failed: ${reason}`,
          color: 'red',
          autoClose: 1500,
        });
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
