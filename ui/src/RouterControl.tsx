class LinkBuilder {
  ResourceCreate(resourceName: string): string {
    return `/resource/${resourceName}/create`;
  }
  ResourceDetail(resourceName: string, detailId: string): string {
    return `/resource/${resourceName}/detail/${detailId}`;
  }
  ResourceList(
    resourceName: string,
    filters: { ref: string; op: string; val: string }[],
    sort?: { ref: string; dir: 'asc' | 'desc' }
  ): string {
    // todo: add pagination, filters, etc
    const query = encodeURI(
      JSON.stringify({
        filters,
        sort,
      })
    );
    return `/resource/${resourceName}/list?search=${query}`;
  }

  CustomPage(pageName: string): string {
    return `/page/${pageName}`;
  }
}

export const linkBuilder = new LinkBuilder();
