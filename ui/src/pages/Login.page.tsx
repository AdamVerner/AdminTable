import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Anchor,
  Button,
  Checkbox,
  Container,
  Group,
  Paper,
  PasswordInput,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { authService } from '@/services/auth';

export const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const from = location?.state?.from ?? { location: '/' };

  // if user is already logged in, redirect to the page they came from
  if (authService.isUserLoggedIn()) {
    navigate(from);
  }

  // login form
  const form = useForm({
    initialValues: {
      email: '',
      password: '',
      remember: false,
    },

    validate: {
      email: (value) => (/^\S+@\S+$/.test(value) ? null : 'Invalid email'),
      password: (value) => (value.length > 0 ? null : 'Password is required'),
    },
  });

  const handleSubmit = async (values: { email: string; password: string }) => {
    try {
      await authService.login(values.email, values.password);
      notifications.show({
        title: 'Authentication Success',
        message: 'You have been successfully authenticated',
        color: 'green',
      });
      navigate(from);
    } catch (e: any) {
      setErrorMessage(e.toString());
    }
  };

  return (
    <Container size={420} my={40}>
      <Title ta="center" style={{ fontWeight: 900 }}>
        Welcome back!
      </Title>
      <Text c="dimmed" size="sm" ta="center" mt={5}>
        To continue, please log-in
      </Text>

      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <form
          onSubmit={form.onSubmit(handleSubmit)}
          onChange={() => {
            setErrorMessage('');
          }}
        >
          <TextInput
            label="Email"
            placeholder="username@example.com"
            {...form.getInputProps('email')}
            required
          />
          <PasswordInput
            label="Password"
            placeholder="Your password"
            {...form.getInputProps('password')}
            required
            mt="md"
          />
          {errorMessage && (
            <Text color="red" mt="md">
              {errorMessage}
            </Text>
          )}
          <Group justify="space-between" mt="lg">
            <Checkbox label="Remember me" {...form.getInputProps('remember')} />
            <Anchor component="button" size="sm">
              Forgot password?
            </Anchor>
          </Group>
          <Button type="submit" fullWidth mt="xl">
            Sign in
          </Button>
        </form>
      </Paper>
    </Container>
  );
};
