import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Text, TypographyStylesProvider } from '@mantine/core';
import UserChart from '@/components/UserChart';

export const MarkdownPage = ({ content }: { content: string }) => {
  const code = ({
    node,
    className,
    children,
    ...props
  }: {
    node?: any;
    className?: string;
    children?: React.ReactNode;
  }): React.ReactElement => {
    if (className === 'language-chart') {
      try {
        const data = JSON.parse(children?.toString() ?? '');
        return <UserChart {...data} />;
      } catch (e: any) {
        return <Text c="red">Error rendering chart: {e?.message}</Text>;
      }
    }
    if (className === 'language-leaflet') {
      const data = JSON.parse(children?.toString() ?? '');
      return (
        <div className="w-100">
          <h3>{data?.title ?? ''}</h3>
          <pre>
            <big>
              <strong>TODO: </strong>
            </big>
            {JSON.stringify(data)}
          </pre>
        </div>
      );
    }

    return (
      <code className={className} {...props}>
        {content}
      </code>
    );
  };

  const pre = ({
    node,
    children,
    ...props
  }: {
    node?: any;
    className?: string;
    children?: React.ReactNode;
  }): React.ReactElement => {
    if (((children as any)?.props?.className ?? '') === 'language-chart') {
      return <div>{children}</div>;
    }

    return <pre {...props}>{children}</pre>;
  };

  return (
    <TypographyStylesProvider>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre,
          code,
        }}
      >
        {content}
      </Markdown>
    </TypographyStylesProvider>
  );
};
