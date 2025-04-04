import { useState } from 'react';
import { IconChevronRight } from '@tabler/icons-react';
import { Link } from 'react-router-dom';
import { Box, Collapse, Group, rem, ThemeIcon, UnstyledButton } from '@mantine/core';
import UserDefinedIcon from '@/components/UserDefinedIcon';
import classes from './NavbarLinksGroup.module.css';

interface ChildLinkProps {
  name: string;
  display: string;
  type: 'resource' | 'page';
}
export function ChildLink(child: ChildLinkProps) {
  const href = (() => {
    switch (child.type) {
      case 'page':
        return `/page/${child.name}`;
      case 'resource':
        return `/resource/${child.name}/list`;
      default:
        throw new Error(`Unknown child type: ${child.type}`);
    }
  })();
  return (
    <Link
      className={classes.link}
      to={href}
      key={child.name}
      // onClick={(event) => event.preventDefault()}
    >
      {child.display}
    </Link>
  );
}

export interface LinksGroupProps {
  name: string;
  icon: string;
  links: ChildLinkProps[];
}
export function LinksGroup({ name, icon, links }: LinksGroupProps) {
  const [opened, setOpened] = useState(false);
  const items = links.map((link) => <ChildLink {...link} key={link.name} />);

  return (
    <>
      <UnstyledButton onClick={() => setOpened((o) => !o)} className={classes.control}>
        <Group justify="space-between" gap={0}>
          <Box style={{ display: 'flex', alignItems: 'center' }}>
            <ThemeIcon variant="light" size={30}>
              <UserDefinedIcon icon={icon} />
            </ThemeIcon>
            <Box ml="md">{name}</Box>
          </Box>
          <IconChevronRight
            className={classes.chevron}
            stroke={1.5}
            style={{
              width: rem(16),
              height: rem(16),
              transform: opened ? 'rotate(-90deg)' : 'none',
            }}
          />
        </Group>
      </UnstyledButton>
      <Collapse in={opened}>{items}</Collapse>
    </>
  );
}
