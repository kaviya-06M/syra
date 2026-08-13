import { useSYRA } from '../context/SYRAContext';

export function useChat() {
	const { messages, sendMessage, clearMessages, isThinking } = useSYRA();
	return {
		messages,
		sendMessage,
		clearMessages,
		isThinking,
	};
}
