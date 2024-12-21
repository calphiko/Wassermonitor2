export function formatDateForInput(date) {
   const year = date.getFullYear();
   const month = String(date.getMonth() + 1).padStart(2, "0");
   const day = String(date.getDate()).padStart(2, "0");
   const hours = String(date.getHours()).padStart(2, "0");
   const minutes = String(date.getMinutes()).padStart(2, "0");
   return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function formatDateForISO(dateString) {
    return new Date(dateString).toISOString().replace("Z","+00:00"); // ISO-Format sicherstellen
 }

export async function getChartIntances() {
    let chartInstances = {
         'fillChart': document.getElementById('fillChart'),
         'timeChart': document.getElementById('TimeChart'),
         'derivChart':  document.getElementById('derivChart')
        };
    return chartInstances;
}

export async function fetchChartConfig(url) {
    try {
        const response_cConfig = await fetch(url);
        if (!response_cConfig.ok) {
            throw new Error ("No response from cConfig-JSON");
        }
        const cConfig = await response_cConfig.json();
        return cConfig;
        //console.log('Color Gradients:',colorGradients);
    } catch(error) {
        console.error('Error while fetching colors!',error);
    }
}