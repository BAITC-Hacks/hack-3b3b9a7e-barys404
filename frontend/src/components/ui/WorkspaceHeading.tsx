export function WorkspaceHeading({ title, text }: { title: string; text: string }) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow">РАБОЧИЙ КАБИНЕТ</div>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>
    </div>
  )
}
