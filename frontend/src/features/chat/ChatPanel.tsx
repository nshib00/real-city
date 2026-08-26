const chatMessages = [
  ['Лидер', 'Собираем кирпичи на мостовую к руинам.'],
  ['Офицер', 'Нефтяная скважина на юге свободна.'],
  ['Участник', 'Отправил древесину в союзную казну.'],
] as const

export function ChatPanel() {
  return (
    <>
      {chatMessages.map(([author, message]) => (
        <p key={`${author}:${message}`}>
          <strong>{author}</strong> {message}
        </p>
      ))}
    </>
  )
}
