import { useEffect, useState } from 'react';
import { Group, Indicator, Tooltip } from '@mantine/core';
import Extendable from '@/components/DataField/Extendable';
import ValueHistory from '@/components/DataField/ValueHistory';
import dataService from '@/services/data.service';

export interface LiveValueProps {
  initial: string;
  topic: string;
  history: boolean;
  title?: string;
}

export default ({ initial, topic, history, title }: LiveValueProps) => {
  const [value, setValue] = useState(initial);
  const [state, setState] = useState<'connecting' | 'connected' | 'failed'>('connecting');
  const [reconnect, setReconnect] = useState(0);

  useEffect(() => {
    setState('connecting');
    let ws;
    try {
      ws = dataService.getLiveDataSocket(topic);
    } catch (e) {
      setState('failed');
      return;
    }

    ws.onopen = () => setState('connected');
    ws.onclose = () => setState('failed');
    ws.onmessage = (ev) => setValue(`${JSON.parse(ev.data)?.value}`);
    ws.onerror = () => {
      setState('failed');
      ws.close();
    };

    return () => {
      ws.close();
    };
  }, [topic, reconnect]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (state === 'failed') {
        setReconnect(reconnect + 1);
      }
    }, 5000);
    return () => {
      clearInterval(interval);
    };
  }, [topic, state]);

  const color = {
    connecting: 'gray',
    connected: 'green',
    failed: 'red',
  }[state];

  const label = {
    connecting: 'Connecting',
    connected: 'Connected, receiving data',
    failed: 'Failed. Cannot connect to the server',
  }[state];

  return (
    <Group>
      <Tooltip label={label}>
        <Indicator zIndex={99} processing color={color} position="top-start">
          <Extendable title={title} value={value} />
        </Indicator>
      </Tooltip>
      {history && <ValueHistory value={value} />}
    </Group>
  );
};
