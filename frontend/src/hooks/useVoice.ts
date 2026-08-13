import { useSYRA } from '../context/SYRAContext';

export function useVoice() {
	const { isListening, isSpeaking, startListening, stopListening, speakText, stopSpeaking } = useSYRA();
	return {
		isListening,
		isSpeaking,
		startListening,
		stopListening,
		speakText,
		stopSpeaking,
	};
}
