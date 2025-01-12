import { IconChevronRight, IconLogout, IconSettings, IconUser } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { Avatar, Group, Menu, rem, Text, UnstyledButton } from '@mantine/core';
import Loader from '@/components/Loader';
import { useUserInfoStore } from '@/stores/user.store';
import classes from './UserButton.module.css';

export const UserButton = () => {
  const navigate = useNavigate();
  const user_info = useUserInfoStore((state) => state.user_info);
  const load_user_info = useUserInfoStore((state) => state.load_user_info);

  if (!user_info) {
    load_user_info().then();
    return <Loader />;
  }

  return (
    <Menu
      withArrow
      width={300}
      position="right"
      transitionProps={{ transition: 'pop' }}
      withinPortal
      trigger="click-hover"
    >
      <Menu.Target>
        <UnstyledButton w="100%" p="md" className={classes.user}>
          <Group>
            <Avatar src={user_info?.avatar_src} radius="xl" />
            <div style={{ flex: 1 }}>
              <Text size="sm" fw={500}>
                {user_info.display}
              </Text>
              <Text c="dimmed" size="xs">
                {user_info?.email}
              </Text>
            </div>

            <IconChevronRight style={{ width: rem(14), height: rem(14) }} stroke={1.5} />
          </Group>
        </UnstyledButton>
      </Menu.Target>
      <Menu.Dropdown>
        {user_info?.has_profile_setting && (
          <Menu.Item
            leftSection={<IconUser style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
            onClick={() => {
              navigate('/profile');
            }}
          >
            User profile
          </Menu.Item>
        )}
        <Menu.Item
          leftSection={<IconSettings style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
          onClick={() => {
            navigate('/settings');
          }}
        >
          Settings
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item
          leftSection={<IconLogout style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
          onClick={() => {
            navigate('/logout');
          }}
        >
          Logout
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
};
