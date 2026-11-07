package com.yourcompany.secretary.tenantservice.api;

// A record is a Java type for carrying data. Java generates its constructor and accessors for us.
//This response deliberately contains only information needed for the greeting. Return only what the caller of that API needs.
//Spring converts the returned record into JSON. Spring MVC documentation.

public record TenantConfigurationResponse(
        String tenantId,
        String businessName,
        String language,
        String timeZone,
        String greeting) {}