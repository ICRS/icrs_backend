import useForm from "./UseForm";
import FORM_ENDPOINT from "./../settings.json";


export const Form = () => {
    const { handleSubmit, status, message } = useForm({});
	console.log(FORM_ENDPOINT.FORM_ENDPOINT)
    return (
        <form
            action={FORM_ENDPOINT.FORM_ENDPOINT}
            onSubmit={handleSubmit}
            method="POST"
        >
            <div className="pt-0 mb-3">
                <label>Card UID:</label>
                <input
                    type="text"
                    name="id"
                    className="focus:outline-none focus:ring relative w-full px-3 py-3 text-sm text-gray-600 placeholder-gray-400 bg-white border-0 rounded shadow outline-none"
                    required
                />
            </div>

            <div className="pt-0 mb-3">
                <label>Shortcode:</label>
                <input
                    type="text"
                    name="shortcode"
                    className="focus:outline-none focus:ring relative w-full px-3 py-3 text-sm text-gray-600 placeholder-gray-400 bg-white border-0 rounded shadow outline-none"
                    required
                />
            </div>

            <div className="pt-0 mb-3">
                <label>Secret:</label>
                <input
                    type="password"
                    name="secret"
                    required
                />
            </div>

            <div className="pt-0 mb-3">
                <label>Can Laser Cut:</label>
                <input
                    type="text"
                    name="canLaserCut"
                    required
                    placeholder="False"
                />
            </div>

            <div className="pt-0 mb-3">
                <label>Can Print:</label>
                <input
                    type="text"
                    name="canPrint"
                    required
                    placeholder="True"
                />
            </div>

            {status !== "loading" && (

                <div className="pt-0 mb-3">
                    <button
                        className="active:bg-blue-600 hover:shadow-lg focus:outline-none px-6 py-3 mb-1 mr-1 text-sm font-bold text-white uppercase transition-all duration-150 ease-linear bg-blue-500 rounded shadow outline-none"
                        type="submit"
                    >
                        Submit
                    </button>
                </div>
            )}
        </form>
    );
};

export default Form;
