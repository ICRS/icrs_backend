function Form(props) {
    const handleSubmit = (e) => {
        e.preventDefault();

        const finalFormEndpoint = e.target.action;
        // console.log("Endpoint", finalFormEndpoint);
        const data = Array.from(e.target.elements)
            .filter((input) => input.name)
            .reduce((obj, input) => Object.assign(obj, { [input.name]: input.value }), {});

        fetch(finalFormEndpoint, {
            method: 'POST',
            headers: {
                "Accept": "*/*",
            },
            body: JSON.stringify(data)
        })
            .then((response) => {
                if (!response.ok) {
                    return alert('User may not be registered.');
                }
            }).catch(() => {
                return alert('Could not submit form. Please try again later. Network or Server error likely.');
            });

    }

    return (
        <div className="form-box">
            <form
                action={props.endpoint}
                onSubmit={handleSubmit}
                method="POST"
                className="table-form" >
                <div className="pt-0 mb-3">
                    <label>Shortcode:</label>
                    <input
                        type="text"
                        name="shortcode" />
                </div>

                <div>
                    <label> Can Print: </label>
                    <select id="canPrint" name="canPrint">
                        <option value="True">True</option>
                        <option value="">False</option>
                    </select>
                </div>

                <div className="pt-0 mb-3">
                    <label>Can Laser Cut:</label>
                    <select id="canLaserCut" name="canLaserCut">
                        <option value="">False</option>
                        <option value="True">True</option>
                    </select>
                </div>
                <div>
                    <button type="submit">Submit</button>
                </div>
            </form>
        </div>
    );
};

function UpdatePermissions(props) {
    return (
        <div>
            <Form endpoint={props.endpoint} />
        </div>
    );
}

export default UpdatePermissions;
