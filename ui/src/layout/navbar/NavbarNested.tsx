import { ScrollArea } from '@mantine/core';
import { LinksGroup, LinksGroupProps } from './NavbarLinksGroup';
import { UserButton } from './UserButton';
import classes from './NavbarNested.module.css';

interface NavbarNestedProps {
  navigationLinks: LinksGroupProps[];
}

export const NavbarNested = ({ navigationLinks }: NavbarNestedProps) => {
  const links = navigationLinks.map((link) => (
    <LinksGroup name={link.name} children={link.children} key={link.name} />
  ));

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
