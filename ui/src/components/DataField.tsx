import { Link } from 'react-router-dom';
import { linkBuilder } from '@/RouterControl';

export interface DataFieldProps {
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
      };
}

export default ({ cell }: DataFieldProps) => {
  if (typeof cell !== 'object' || !cell) {
    return `${cell}`;
  }
  if (cell.type === 'link' && cell.kind === 'detail') {
    return <Link to={linkBuilder.ResourceDetail(cell.resource, cell.id)}>{cell.value}</Link>;
  }
  if (cell.type === 'link' && cell.kind === 'table') {
    return (
      <Link
        to={linkBuilder.ResourceList(cell.resource, [
          { ref: cell.filter.col, op: cell.filter.op, val: cell.filter.val },
        ])}
      >
        {cell.value}
      </Link>
    );
  }
  return JSON.stringify(cell);
};
