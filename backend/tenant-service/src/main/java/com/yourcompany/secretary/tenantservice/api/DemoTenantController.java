package com.yourcompany.secretary.tenantservice.api;

import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

//| `@RestController` | Makes this class handle HTTP requests and return response data. |
//| `@Profile("local")` | Enables this demo controller only when the `local` profile is active. |
//| `@RequestMapping` | Defines the shared URL prefix. |
//| `@GetMapping` | Maps an HTTP GET request to this method. |

@RestController
@Profile("local")
@RequestMapping("/api/v1/demo")
public class DemoTenantController {

    @GetMapping("/tenant-configuration")
    public TenantConfigurationResponse getTenantConfiguration() {
        return new TenantConfigurationResponse(
                "demo-salon",
                "Demo Salon",
                "el-GR",
                "Europe/Athens",
                "Hello, you have reached Demo Salon. "
                        + "I am the AI receptionist. How can I help?"
        );
    }
}
