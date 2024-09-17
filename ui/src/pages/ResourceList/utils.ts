import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

interface SearchState {
  page: number;
  perPage: number;
  sort?: { ref: string; dir: 'asc' | 'desc' };
  filters: { ref: string; op: string; val: string }[];
}

const SEARCH_KEY = 'search';
const DEFAULT_STATE: SearchState = { page: 1, perPage: 50, filters: [] };

const safeParse = (str: string | null): SearchState => {
  if (!str) {
    return DEFAULT_STATE;
  }
  try {
    const tmp = JSON.parse(str);
    if (typeof tmp !== 'object') {
      return DEFAULT_STATE;
    }
    if (typeof tmp.page !== 'number') {
      tmp.page = DEFAULT_STATE.page;
    }
    if (typeof tmp.perPage !== 'number') {
      tmp.perPage = DEFAULT_STATE.perPage;
    }
    if (!Array.isArray(tmp.filters)) {
      tmp.filters = DEFAULT_STATE.filters;
    }
    return tmp;
  } catch {
    return DEFAULT_STATE;
  }
};

export const useTableParams = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const params = searchParams.get(SEARCH_KEY);
  const [state, setState] = useState<SearchState>(safeParse(params));

  useEffect(() => {
    const newState = safeParse(params);
    if (JSON.stringify(newState) !== JSON.stringify(state)) {
      setState(newState);
    }
  }, [params]);

  useEffect(() => {
    if (JSON.stringify(state) !== JSON.stringify(safeParse(params))) {
      setSearchParams({ [SEARCH_KEY]: JSON.stringify(state) });
    }
  }, [state]);

  const setPage = (page: number): void => {
    setState({ ...state, page });
  };

  const setPerPage = (perPage: number): void => {
    setState({ ...state, page: 1, perPage });
  };

  const setSort = (sort: { ref: string; dir: 'asc' | 'desc' }): void => {
    setState({ ...state, sort, page: 1 });
  };

  const setFilters = (filters: { ref: string; op: string; val: string }[]): void => {
    setState({ ...state, filters, page: 1 });
  };

  return { state, setPage, setPerPage, setSort, setFilters };
};
