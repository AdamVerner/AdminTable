import { Outlet, useNavigate } from 'react-router-dom';
import { AppShell, Burger, Center, Code, Group, Loader, Text } from '@mantine/core';
import { useDisclosure, useDocumentTitle } from '@mantine/hooks';
import ColorSchemeToggle from '@/components/ColorSchemeToggle/ColorSchemeToggle';
import { Logo } from '@/components/Logo';
import { NavbarNested } from '@/layout/navbar/NavbarNested';
import dataService, { useGetData } from '@/services/data.service';

export const Layout = () => {
  const [opened, { toggle }] = useDisclosure();
  const navigate = useNavigate();
  const [navigation, navigationLoading] = useGetData(
    async () => await dataService.getNavigation(),
    []
  );

  const goHome = () => navigate('/');

  useDocumentTitle(navigation?.name || '');

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
          <Group justify="space-between" onClick={goHome} style={{ cursor: 'pointer' }}>
            <Logo src={navigation.icon_src} />
            <Text>{navigation.name}</Text>
            {navigation.version && <Code>{navigation.version}</Code>}
          </Group>
          <Group ml="auto">
            <ColorSchemeToggle />
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar>
        <NavbarNested navigation={navigation.navigation} />
      </AppShell.Navbar>
      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
};
