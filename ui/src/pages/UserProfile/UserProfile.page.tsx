import { useState } from 'react';
import {
  Avatar,
  Box,
  Button,
  Container,
  FileButton,
  Grid,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import dataService from '@/services/data.service';
import { useUserInfoStore } from '@/stores/user.store';

const toBase64 = (file: File) =>
  new Promise<string | ArrayBuffer | null>((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
  });

const AvatarUploadButton = () => {
  const [status, setStatus] = useState<null | 'uploading'>(null);
  const load_user_info = useUserInfoStore((state) => state.load_user_info);

  const uploadFile = async (f: File | null) => {
    if (f !== null) {
      setStatus('uploading');
      const data = (await toBase64(f)) as string;
      await dataService.setUserInfo({ avatar_src: data });
      await load_user_info();
    }
    setStatus(null);
  };

  return (
    <Group>
      <FileButton onChange={uploadFile} accept="image/png,image/jpeg">
        {(props) => <Button {...props}>Choose file...</Button>}
      </FileButton>
      <span>{status === 'uploading' && <Loader size="xs" />}</span>
    </Group>
  );
};

const AvatarUpload = () => {
  const user = useUserInfoStore((state) => state.user_info);

  if (!user) {
    return <Loader />;
  }
  return (
    <>
      <Grid.Col span={4}>
        <Title order={2}>Avatar</Title>
        <Text>You can change your public avatar here.</Text>
      </Grid.Col>
      <Grid.Col span={8}>
        <Group align="start">
          <Avatar src={user?.avatar_src} size={150} radius="xl" />
          <Stack justify="start">
            <Title order={3} size="h4">
              Upload new avatar
            </Title>
            <Box>
              <AvatarUploadButton />
            </Box>
            <Text>The maximum file size allowed is 200KB.</Text>
          </Stack>
        </Group>
      </Grid.Col>
    </>
  );
};

export const UserProfilePage = () => {
  const user_info = useUserInfoStore((state) => state.user_info);

  if (!user_info) {
    return <Loader />;
  }

  return (
    <Container w="100%">
      <Title order={1} mb="md">
        User profile
      </Title>
      <Grid>
        <AvatarUpload />
      </Grid>
    </Container>
  );
};
