import { Link } from 'react-router-dom';
import { linkBuilder } from '@/RouterControl';
import Extendable from './Extendable';
import LiveValue from './LiveValue';

export interface FieldProps {
  title?: string;
  cell:
    | string
    | number
    | boolean
    | {
        type: 'link';
        kind: 'detail';
        resource: string;
        value: string;
        id: string;
      }
    | {
        type: 'link';
        kind: 'table';
        resource: string;
        value: string;
        filter: {
          col: string;
          op: string;
          val: string;
        };
      }
    | {
        type: 'live';
        initial: string;
        topic: string;
        history: boolean;
      };
}

export default ({ cell, title }: FieldProps) => {
  if (typeof cell !== 'object' || !cell) {
    return <Extendable title={title} value={`${cell}`} />;
  }
  if (cell.type === 'link' && cell.kind === 'detail') {
    if (!cell.resource || !cell.id) {
      return <Extendable title={title} value="" />;
    }
    return (
      <Link to={linkBuilder.ResourceDetail(cell.resource, cell.id)}>
        <Extendable title={title} value={cell.value} />
      </Link>
    );
  }
  if (cell.type === 'link' && cell.kind === 'table') {
    return (
      <Link
        to={linkBuilder.ResourceList(cell.resource, [
          { ref: cell.filter.col, op: cell.filter.op, val: cell.filter.val },
        ])}
      >
        <Extendable title={title} value={cell.value} />
      </Link>
    );
  }
  if (cell.type === 'live') {
    return (
      <LiveValue initial={cell.initial} topic={cell.topic} history={cell.history} title={title} />
    );
  }
  return JSON.stringify(cell);
};
