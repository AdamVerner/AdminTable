import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { LineChart } from '@mantine/charts';
import { TypographyStylesProvider } from '@mantine/core';

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
    if (className === 'language-recharts') {
      const data = JSON.parse(children?.toString() ?? '');
      return (
        <div className="w-100">
          <h3>{data?.title ?? ''}</h3>
          <LineChart data={data.data} {...data} redraw />
        </div>
      );
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
    if (((children as any)?.props?.className ?? '') === 'language-chartjs') {
      return <div className="col col-md-6 mx-auto">{children}</div>;
    }
    if (((children as any)?.props?.className ?? '') === 'language-leaflet') {
      return <div className="col col-md-6 mx-auto">{children}</div>;
    }
    return <pre {...props}>{children}</pre>;
  };

  return (
    <TypographyStylesProvider>
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ node, ...rest }) => <p style={{ marginBottom: 'initial' }} {...rest} />,
          pre,
          code,
        }}
      >
        {content}
      </Markdown>
    </TypographyStylesProvider>
  );
};
