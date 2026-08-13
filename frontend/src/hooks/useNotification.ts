import { useSYRA } from '../context/SYRAContext';

export function useNotification() {
	const { showNotification, notificationAnomaly, dismissNotification, openAnomalyFromNotification } = useSYRA();
	return {
		showNotification,
		notificationAnomaly,
		dismissNotification,
		openAnomalyFromNotification,
	};
}
