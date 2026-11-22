export type BoardColumn = {
  key: string;
  label: string;
  is_finished?: boolean;
};

export const BASIC_TASK_COLUMNS: BoardColumn[] = [
  { key: "todo", label: "Todo" },
  { key: "in_progress", label: "In progress" },
  { key: "blocked", label: "Blocked" },
  { key: "done", label: "Done", is_finished: true },
  { key: "cancelled", label: "Cancelled", is_finished: true },
];

export function resolveTaskColumns(rows: BoardColumn[] | undefined): BoardColumn[] {
  return rows && rows.length > 0 ? rows : BASIC_TASK_COLUMNS;
}
