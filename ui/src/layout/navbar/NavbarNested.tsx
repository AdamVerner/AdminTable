import { ScrollArea } from '@mantine/core';
import { LinksGroup, LinksGroupProps } from './NavbarLinksGroup';
import { UserButton } from './UserButton';
import classes from './NavbarNested.module.css';

interface NavbarNestedProps {
  navigation: LinksGroupProps[];
}

export const NavbarNested = ({ navigation }: NavbarNestedProps) => {
  const links = navigation.map((nav) => {
    if (nav.links.length === 0) {
      return null;
    }
    return <LinksGroup name={nav.name} links={nav.links} key={nav.name} />;
  });

  return (
    <nav className={classes.navbar}>
      <ScrollArea className={classes.links}>
        <div className={classes.linksInner}>{links}</div>
      </ScrollArea>

      <div className={classes.footer}>
        <UserButton />
      </div>
    </nav>
  );
};
