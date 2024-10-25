import { useParams } from 'react-router-dom';
import { Center, Loader } from '@mantine/core';
import SubmittableForm from '@/components/SubmittableForm';
import { useTableParams } from '@/pages/ResourceList/utils';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const { state: SearchState } = useTableParams();
  const { resourceName } = useParams();

  const [data, isLoading, failed] = useGetData(async () => {
    return await dataService.getCreate(resourceName!);
  }, [resourceName, JSON.stringify(SearchState)]);

  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  const onSubmit = async (data: any) => {
    return await dataService.createResource(resourceName!, data);
  };

  return <SubmittableForm schema={data.schema} onSubmit={onSubmit} />;
};
