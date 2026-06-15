/**
 * Registro unico de Chart.js para los graficos de linea de metricas.
 * Se importa por efecto colateral desde cada componente de grafico.
 */
import {
    Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, Filler,
} from 'chart.js'

ChartJS.register(
    CategoryScale, LinearScale, PointElement, LineElement,
    Title, Tooltip, Legend, Filler
)