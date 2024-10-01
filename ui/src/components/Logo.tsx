import { useEffect } from 'react';
import { rem } from '@mantine/core';

interface LogoProps {
  src: string | null;
}

export function Logo(props: LogoProps) {
  useEffect(() => {
    const link: any = document.querySelector("link[rel~='icon']");
    link.href = props.src;
  }, [props.src]);

  const style = { height: rem(50) };
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
