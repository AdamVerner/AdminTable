import { Navigate, useLocation, useParams } from 'react-router-dom';
import { Center, Container, Loader } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import SubmittableForm from '@/components/SubmittableForm';
import dataService, { useGetData } from '@/services/data.service';

export default () => {
  const { formName } = useParams();
  const location = useLocation();

  const [data, isLoading, failed] = useGetData(
    async () => await dataService.getInputForm(formName!),
    []
  );

  if (failed && !isLoading && failed.includes('Unauthorized')) {
    notifications.show({
      title: 'Please log in',
      message: `To view the form, please log in.`,
      color: 'red',
      autoClose: 15000,
    });
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (isLoading || !data || failed) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  const onsubmit = async (data: any) => {
    return await dataService.submitInputForm(formName!, data);
  };

  return (
    <Container>
      <SubmittableForm title={data.title} schema={data.schema} onSubmit={onsubmit} />
    </Container>
  );
};
