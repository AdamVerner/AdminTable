import { IconMoonStars, IconSun } from '@tabler/icons-react';
import { rem, Switch, useMantineColorScheme, useMantineTheme } from '@mantine/core';

export default () => {
  const theme = useMantineTheme();
  const { toggleColorScheme } = useMantineColorScheme();

  const sunIcon = (
    <IconSun
      style={{ width: rem(16), height: rem(16) }}
      stroke={2.5}
      color={theme.colors.yellow[4]}
    />
  );

  const moonIcon = (
    <IconMoonStars
      style={{ width: rem(16), height: rem(16) }}
      stroke={2.5}
      color={theme.colors.blue[6]}
    />
  );

  return (
    <Switch
      onClick={() => toggleColorScheme()}
      size="md"
      color="dark.4"
      onLabel={sunIcon}
      offLabel={moonIcon}
    />
  );
};
