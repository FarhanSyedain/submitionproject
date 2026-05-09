const PILLS = {
  pending: { label: 'Pending', cls: 'pill' },
  running: { label: 'Running', cls: 'pill pill-warn' },
  completed: { label: 'Done', cls: 'pill pill-good' },
  failed: { label: 'Failed', cls: 'pill pill-bad' },
}

export default function StatusPill({ status }) {
  const meta = PILLS[status] || { label: status, cls: 'pill' }
  return <span className={meta.cls}>{meta.label}</span>
}
