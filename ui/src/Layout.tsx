import { Outlet } from 'react-router-dom';
import { AppShell, Burger, Center, Code, Group, Loader, rem, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import ColorSchemeToggle from '@/components/ColorSchemeToggle/ColorSchemeToggle';
import { NavbarNested } from '@/layout/navbar/NavbarNested';
import dataService, { useGetData } from '@/services/data.service';
import { Logo } from './Logo';

export const Layout = () => {
  const [opened, { toggle }] = useDisclosure();
  const [navigation, navigationLoading] = useGetData(
    async () => await dataService.getNavigation(),
    []
  );

  if (navigationLoading || !navigation) {
    return (
      <Center style={{ height: '100vh' }}>
        <Loader size="xl" />
      </Center>
    );
  }

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 300, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md">
          <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
          <Group justify="space-between">
            <Logo style={{ width: rem(120) }} />
            <Text>{navigation.name}</Text>
            <Code fw={700}>v0.1.2</Code>
          </Group>
          <Group ml="auto">
            <ColorSchemeToggle />
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar>
        <NavbarNested navigationLinks={navigation.links} />
      </AppShell.Navbar>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
};
