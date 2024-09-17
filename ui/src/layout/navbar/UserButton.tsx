import {IconChevronRight, IconLogout} from '@tabler/icons-react';
import {Avatar, Group, Loader, Menu, rem, Text, UnstyledButton} from '@mantine/core';
import classes from './UserButton.module.css';
import {useNavigate} from "react-router-dom";
import dataService, {useGetData} from "@/services/data.service";

export function UserButton() {
  const navigate = useNavigate();
  const [data, isLoading] = useGetData(
    async () => await dataService.getUserInfo(),
    []
  );

  if (isLoading || !data) {
    return (
      <Loader/>
    );
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
    <UnstyledButton w="100%" p='md' className={classes.user}>
      <Group>
        <Avatar
          src={data.user?.avatar ?? 'https://raw.githubusercontent.com/mantinedev/mantine/master/.demo/avatars/avatar-8.png'}
          radius="xl"
        />

        <div style={{ flex: 1 }}>
          {data.user?.name ? (
              <>
          <Text size="sm" fw={500}>{data.user?.name}</Text>
              <Text c="dimmed" size="xs">
                {data.user.email}
          </Text>
              </>

          ): (
              <Text  size="sm" fw={500}>
                {data.user.email}
          </Text>
          )
          }
        </div>

        <IconChevronRight style={{ width: rem(14), height: rem(14) }} stroke={1.5} />
      </Group>
    </UnstyledButton></Menu.Target>
        <Menu.Dropdown>
          <Menu.Item
            leftSection={<IconLogout style={{ width: rem(16), height: rem(16) }} stroke={1.5} />}
            onClick={()=>{navigate('/logout')}}
          >
            Logout
          </Menu.Item>
        </Menu.Dropdown>
      
      </Menu>
  );
}
