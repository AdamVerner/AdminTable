import { NavigateFunction } from 'react-router/dist/lib/hooks';
import { notifications } from '@mantine/notifications';
import { linkBuilder } from '@/RouterControl';

interface actionResponse {
  message: string;
  failed?: boolean;
  refresh?: boolean;
  redirect?:
    | { type: 'detail'; resource: string; id: string }
    | { type: 'list'; resource: string; filters: { ref: string; op: string; val: string }[] }
    | { type: 'customPage'; name: string };
}

export default async (action: Promise<actionResponse>, navigate: NavigateFunction) => {
  return action
    .then((resp) => {
      notifications.show({
        title: resp.failed ? 'Failed' : 'Success',
        message: resp.message,
        color: resp.failed ? 'red' : 'blue',
      });
      if (resp?.redirect) {
        if (resp.redirect.type === 'detail') {
          navigate(linkBuilder.ResourceDetail(resp.redirect.resource, resp.redirect.id));
        } else if (resp.redirect.type === 'list') {
          navigate(linkBuilder.ResourceList(resp.redirect.resource!, resp.redirect.filters));
        } else if (resp.redirect.type === 'customPage') {
          navigate(linkBuilder.CustomPage(resp.redirect.name));
        }
      }
      return resp;
    })
    .catch((error) => {
      notifications.show({
        title: 'Failed',
        message: `Failed: ${error}`,
        color: 'red',
        autoClose: 15000,
      });
    });
};
