import warnings

from h2integrate.core.model_baseclasses import PerformanceModelBaseClass


class WindPerformanceBaseClass(PerformanceModelBaseClass):
    _time_step_bounds = (
        3600,
        3600,
    )  # (min, max) time step lengths (in seconds) compatible with this model

    def initialize(self):
        super().initialize()
        self.commodity = "electricity"
        self.commodity_rate_units = "kW"
        self.commodity_amount_units = "kW*h"

    def setup(self):
        super().setup()

        self.add_discrete_input(
            "wind_resource_data",
            val={},
            desc="Wind resource data dictionary",
        )

    def calculate_bounding_heights_from_resource_data(
        self, hub_height_meters, resource_data, resource_vars=["wind_speed"]
    ):
        """This method finds the wind resource heights that bound the turbine hub-height.
        This method returns resource heights (`height_1` and/or `height_2`) that are closest
        to the turbine hub-height and where ``height_1 < hub_height_meters < height_2`` OR
        ``height_1 == hub_height_meters``.

        Note:
            This function assumes resource heights are integers. This function also assumes
            that all variables in ``resource_vars`` have the same resource heights.
            If the hub height exceeds the maximum available resource height, that maximum
            is returned with a warning and no vertical extrapolation is applied.

        Args:
            hub_height_meters (int | float): turbine hub-height in meters
            resource_data (dict): wind resource data dictionary.
            resource_vars (list[str], optional): Wind resource data types
                used to find the bounding resource heights. Defaults to
                ["wind_speed"].

        Returns:
            list[int]: list of resource heights in meters that most closely bound
                the turbine hub-height.

        Raises:
            ValueError: If no resource heights exist for the requested variables.
        """
        heights_per_parameter = {}
        allowed_hub_height_meters = set()
        # get a list of resource heights from the wind resource dictionary
        # for the resource parameters `resource_vars`
        for param in resource_vars:
            params_heights = [
                int(k.split("_")[-1].replace("m", "").strip())
                for k, v in resource_data.items()
                if param in k and "m" in k.split("_")[-1]
            ]
            if len(params_heights) > 0:
                heights_per_parameter.update({param: params_heights})
                allowed_hub_height_meters.update(params_heights)

        if not allowed_hub_height_meters:
            raise ValueError(
                "No wind resource heights were found for variables "
                f"{resource_vars}."
            )

        maximum_resource_height = max(allowed_hub_height_meters)
        if float(hub_height_meters) > float(maximum_resource_height):
            warnings.warn(
                (
                    f"Requested hub height {float(hub_height_meters):g} m exceeds the "
                    f"maximum available wind resource height {maximum_resource_height:g} m; "
                    f"using {maximum_resource_height:g} m without vertical extrapolation."
                ),
                UserWarning,
                stacklevel=2,
            )
            return [int(maximum_resource_height)]

        # Check if any resource height is equal to the hub-height
        if any(float(hh) == float(hub_height_meters) for hh in allowed_hub_height_meters):
            return [int(hub_height_meters)]
        # Find the bounding hub-heights
        # Find the resource heights below the turbine height
        heights_lower = [hh for hh in allowed_hub_height_meters if hh / hub_height_meters < 1]
        # Find the resource heights above the turbine height
        heights_upper = [hh for hh in allowed_hub_height_meters if hh / hub_height_meters > 1]
        # Select the lower-bound resource height as the one closest to `hub_height_meters`
        height_low = (
            max(heights_lower) if len(heights_lower) > 0 else min(allowed_hub_height_meters)
        )
        # Select the upper-bound resource height as the one closest to `hub_height_meters`
        height_high = (
            min(heights_upper) if len(heights_upper) > 0 else max(allowed_hub_height_meters)
        )
        return [int(height_low), int(height_high)]

    def compute(self, inputs, outputs, discrete_inputs, discrete_outputs):
        """
        Computation for the OM component.

        For a template class this is not implement and raises an error.
        """

        raise NotImplementedError("This method should be implemented in a subclass.")
