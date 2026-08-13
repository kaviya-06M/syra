import { useSYRA } from '../context/SYRAContext';

export function useSystemStatus() {
	const { healthState, settings, updateSettings } = useSYRA();
	return {
		healthState,
		isMonitoring: healthState.backgroundMonitoringActive,
		toggleMonitoring: () =>
			updateSettings({
				general: {
					...settings.general,
					backgroundMonitoring: !settings.general.backgroundMonitoring,
				},
			}),
	};
}
