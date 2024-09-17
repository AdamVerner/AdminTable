import { Center, Loader } from '@mantine/core';

export default ({ full = false }: { full?: boolean }) => {
  return (
    <Center style={{ height: full ? '100vh' : undefined }}>
      <Loader size="xl" />
    </Center>
  );
};
