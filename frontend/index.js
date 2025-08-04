async function submitJob() {
    const payload = {
        userId: "demo-user",
        audioChunkPaths: [
            "audio-file-1.wav",
            "audio-file-2.wav",
            "audio-file-3.wav",
            "audio-file-4.wav",
        ],
    };

    document.getElementById("status").innerText = "Submitting job...";
    document.getElementById("transcript").innerText = "";

    try {
        const response = await fetch("http://localhost:8000/transcribe", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        const jobId = data.jobId;
        document.getElementById("status").innerText = `Job submitted. Polling status for jobId: ${jobId}`;

        pollTranscript(jobId);
    } catch (err) {
        document.getElementById("status").innerText = "Error submitting job.";
        console.error(err);
    }
}

async function pollTranscript(jobId) {
    const POLL_INTERVAL = 3000; // ms

    const check = async () => {
        try {
            const res = await fetch(`http://localhost:8000/transcript/${jobId}`);
            const data = await res.json();

            if (data.status === "completed") {
                document.getElementById("status").innerText = "Job completed";
                document.getElementById("transcript").innerText = data.transcriptText;
            } else if (data.status === "failed") {
                document.getElementById("status").innerText = "Job failed";
            } else {
                document.getElementById("status").innerText = `Job status: ${data.status}...`;
                setTimeout(check, POLL_INTERVAL);
            }
        } catch (err) {
            document.getElementById("status").innerText = "Error polling transcript.";
            console.error(err);
        }
    };

    check();
}
