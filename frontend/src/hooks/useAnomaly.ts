import { useSYRA } from '../context/SYRAContext';

export function useAnomaly() {
	const { healthState, triggerAnomalySimulation, resolveActiveAnomaly } = useSYRA();
	return {
		activeAnomaly: healthState.activeAnomaly,
		hasAnomaly: !!healthState.activeAnomaly,
		triggerAnomalySimulation,
		resolveActiveAnomaly,
	};
}
