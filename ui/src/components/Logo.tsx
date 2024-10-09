import { rem } from '@mantine/core';
import { useFavicon } from '@mantine/hooks';

interface LogoProps {
  src: string | null;
}

export function Logo(props: LogoProps) {
  const style = { height: rem(50) };
  useFavicon(props.src || '');

  if (props.src) {
    return <img style={style} src={props.src} alt="logo" />;
  }

  return (
    <svg style={style} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <text y=".9em" font-size="90">
        🚀
      </text>
    </svg>
  );
}
