import React, { useCallback, useEffect, useRef, useState } from "react";
import { messagesApi } from "@/api/endpoints";
import { useAuth } from "@/context/AuthContext";
import { useNotifications } from "@/context/NotificationContext";
import MessageBubble from "@/components/chat/MessageBubble";
import Composer from "@/components/chat/Composer";
import EmptyState from "@/components/common/EmptyState";
import LoadingSpinner from "@/components/common/LoadingSpinner";
import type { Attachment, Message } from "@/types";
import "@/components/chat/Chat.css";

export default function ChatRoom({ ticketId, canPost, disabledReason }: { ticketId: string; canPost: boolean; disabledReason?: string }) {
  const { user } = useAuth();
  const { notifications } = useNotifications();
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [replyTo, setReplyTo] = useState<Message | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    const { data } = await messagesApi.list(ticketId);
    setMessages(data);
  }, [ticketId]);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  useEffect(() => {
    const relevant = notifications.find((n) => n.type === "new_message" && n.ticket_id === ticketId);
    if (relevant) load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [notifications, ticketId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  const handleSend = async (content: string, replyToId: string | null, attachments: Attachment[]) => {
    await messagesApi.send(ticketId, { content, reply_to_message_id: replyToId, attachments });
    await load();
  };

  const handleEdit = async (message: Message, newContent: string) => {
    await messagesApi.edit(ticketId, message.id, newContent);
    await load();
  };

  const handleDelete = async (message: Message) => {
    await messagesApi.remove(ticketId, message.id);
    await load();
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="chat-room" data-testid="chat-room">
      <div className="chat-room-messages">
        {messages.length === 0 ? (
          <EmptyState title="No messages yet" subtitle="Start the conversation below." testId="chat-room-empty" />
        ) : (
          messages.map((m) => (
            <MessageBubble
              key={m.id}
              message={m}
              isMine={m.sender_id === user?.id}
              onReply={setReplyTo}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>
      <Composer
        ticketId={ticketId}
        replyTo={replyTo}
        onClearReply={() => setReplyTo(null)}
        onSend={handleSend}
        disabled={!canPost}
        disabledReason={disabledReason}
      />
    </div>
  );
}
